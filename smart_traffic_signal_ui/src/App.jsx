import { useEffect, useMemo, useRef, useState } from "react";
import { io } from "socket.io-client";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";
const SOCKET_BASE =
  import.meta.env.VITE_SOCKET_BASE_URL || API_BASE.replace(/\/api\/?$/, "");
const SIDES = ["NORTH", "EAST", "SOUTH", "WEST"];

const SIGNAL_COLORS = {
  RED: "bg-rose-500 shadow-rose-400/60",
  YELLOW: "bg-amber-400 shadow-amber-300/70",
  GREEN: "bg-emerald-400 shadow-emerald-300/70",
};

const EMPTY_STATE = {
  running: false,
  speed: 1,
  greenDuration: 15,
  yellowDuration: 4,
  currentSide: "NORTH",
  remainingTime: 0,
  signals: { NORTH: "RED", EAST: "RED", SOUTH: "RED", WEST: "RED" },
  vehicleCounts: { NORTH: 0, EAST: 0, SOUTH: 0, WEST: 0 },
  totalVehicles: 0,
  totalCrossed: 0,
  crossedByType: { CAR: 0, TRUCK: 0, AMBULANCE: 0 },
  emergency: { active: false, side: null, queue: 0, remaining: 0 },
  events: [],
  backendUiEnabled: true,
  backendUiRunning: false,
  vehicles: [],
};

const ADMIN_MENU = [
  { id: "live", label: "Live Monitor" },
  { id: "health", label: "System Health" },
  { id: "audit", label: "Audit Trail" },
  { id: "violations", label: "Violation Reports" },
];

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("trafficAuthToken") || "",
  );
  const [user, setUser] = useState(null);
  const [state, setState] = useState(EMPTY_STATE);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [menuId, setMenuId] = useState("live");
  const [systemHealth, setSystemHealth] = useState(null);
  const [auditTrail, setAuditTrail] = useState([]);
  const [violations, setViolations] = useState(null);
  const [backendUiMessage, setBackendUiMessage] = useState("");
  const socketRef = useRef(null);

  const role = user?.role || "";
  const isAdmin = role === "SYSTEM_ADMIN";
  const canControl = role === "TRAFFIC_PERSONNEL" || role === "SYSTEM_ADMIN";

  const authHeaders = useMemo(
    () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    }),
    [token],
  );

  const logout = async () => {
    try {
      if (token) {
        await fetchJson(`${API_BASE}/auth/logout`, {
          method: "POST",
          headers: authHeaders,
        });
      }
    } catch {
      // Ignore logout API errors and clear local session anyway.
    }

    localStorage.removeItem("trafficAuthToken");
    setToken("");
    setUser(null);
    setState(EMPTY_STATE);
    setConnected(false);
    setError("");
    setMenuId("live");
    setBackendUiMessage("");
  };

  const callControl = async (path, body = {}) => {
    if (!token) {
      return;
    }

    setLoading(true);
    try {
      const payload = await fetchJson(`${API_BASE}${path}`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify(body),
      });
      if (payload.state) {
        setState(payload.state);
      }
      setError("");
    } catch (err) {
      setError(err.message || "Control request failed.");
      if (/unauthorized/i.test(String(err.message))) {
        await logout();
      }
    } finally {
      setLoading(false);
    }
  };

  const syncState = async () => {
    if (!token) {
      return;
    }

    try {
      const payload = await fetchJson(`${API_BASE}/state?t=${Date.now()}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      setState(payload.state || EMPTY_STATE);
      setConnected(true);
      setError("");
    } catch (err) {
      setConnected(false);
      setError(err.message || "Failed to fetch simulation state.");
      if (/unauthorized/i.test(String(err.message))) {
        await logout();
      }
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await syncState();

      if (isAdmin) {
        await loadAdminPanels();
      }

      if (socketRef.current && !socketRef.current.connected) {
        socketRef.current.connect();
      }
    } finally {
      setLoading(false);
    }
  };

  const loadAdminPanels = async () => {
    if (!token || !isAdmin) {
      return;
    }

    try {
      const [healthPayload, auditPayload, violationsPayload] =
        await Promise.all([
          fetchJson(`${API_BASE}/system-health`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetchJson(`${API_BASE}/audit-trail`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          fetchJson(`${API_BASE}/violations-report`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

      setSystemHealth(healthPayload.health || null);
      setAuditTrail(auditPayload.logs || []);
      setViolations(violationsPayload.report || null);
    } catch (err) {
      setError(err.message || "Failed to load admin reports.");
    }
  };

  const openBackendUi = async () => {
    try {
      const payload = await fetchJson(`${API_BASE}/system/open-backend-ui`, {
        method: "POST",
        headers: authHeaders,
      });
      setBackendUiMessage(payload.message || "Simulation UI launch requested.");
      setError("");
      await syncState();
    } catch (err) {
      setBackendUiMessage("");
      setError(err.message || "Failed to open backend simulation UI.");
    }
  };

  useEffect(() => {
    if (!token) {
      return;
    }

    const checkSession = async () => {
      try {
        const payload = await fetchJson(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(payload.user || null);
        setError("");
      } catch {
        await logout();
      }
    };

    checkSession();
  }, [token]);

  useEffect(() => {
    if (!token || !user) {
      return;
    }

    const socket = io(SOCKET_BASE, {
      transports: ["polling"],
      upgrade: false,
      auth: { token },
    });
    socketRef.current = socket;

    socket.on("connect", () => {
      setConnected(true);
      setError("");
    });

    socket.on("disconnect", () => {
      setConnected(false);
    });

    socket.on("connect_error", (err) => {
      setConnected(false);
      setError(err?.message || "Realtime connection failed.");
      if (/unauthorized/i.test(String(err?.message || ""))) {
        logout();
      }
    });

    socket.on("state_update", (payload) => {
      if (payload?.state) {
        setState(payload.state);
        setConnected(true);
      }
    });

    syncState();

    return () => {
      socketRef.current = null;
      socket.disconnect();
    };
  }, [token, user]);

  useEffect(() => {
    if (!token || !user || user.role !== "SYSTEM_ADMIN") {
      return;
    }

    loadAdminPanels();
    const adminPoll = setInterval(() => {
      loadAdminPanels();
    }, 3000);

    return () => clearInterval(adminPoll);
  }, [token, user]);

  const kpis = useMemo(
    () => [
      { label: "Live Vehicles", value: state.totalVehicles },
      { label: "Vehicles Crossed", value: state.totalCrossed },
      { label: "Current Green Side", value: state.currentSide || "N/A" },
      { label: "Timer (sec)", value: Math.ceil(state.remainingTime || 0) },
    ],
    [state],
  );

  if (!user) {
    return (
      <LoginScreen
        onLoginSuccess={(sessionToken, profile) => {
          localStorage.setItem("trafficAuthToken", sessionToken);
          setToken(sessionToken);
          setUser(profile);
        }}
      />
    );
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-[1450px] px-4 py-6 text-slate-100 sm:px-6 lg:px-10">
      <header className="mb-6 rounded-3xl border border-cyan-300/20 bg-slate-900/60 p-6 backdrop-blur-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="title-font text-sm uppercase tracking-[0.3em] text-cyan-300">
              Smart Traffic Signal Automation
            </p>
            <h1 className="title-font mt-2 text-3xl font-bold text-slate-50 sm:text-4xl">
              Role-Based Control and Monitoring
            </h1>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              className="rounded-lg bg-slate-700 px-3 py-2 text-xs uppercase tracking-[0.16em] text-slate-100 hover:bg-slate-600 disabled:cursor-not-allowed disabled:opacity-60"
              onClick={openBackendUi}
              disabled={!state.backendUiEnabled || loading}
              title={
                state.backendUiEnabled
                  ? "Open local desktop simulation window"
                  : "Desktop simulation is disabled in backend environment"
              }
            >
              Open Backend UI
            </button>
            <button
              type="button"
              className="rounded-lg bg-rose-600 px-3 py-2 text-xs uppercase tracking-[0.16em] text-rose-50 hover:bg-rose-500"
              onClick={logout}
            >
              Logout
            </button>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-3 text-xs uppercase tracking-[0.16em]">
          <span className="rounded-full bg-cyan-500/15 px-3 py-1 text-cyan-200">
            User: {user.displayName} ({user.role})
          </span>
          <span
            className={`rounded-full px-3 py-1 ${connected ? "bg-emerald-500/20 text-emerald-200" : "bg-rose-500/20 text-rose-200"}`}
          >
            Backend: {connected ? "Connected" : "Disconnected"}
          </span>
          {state.backendUiRunning && (
            <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-emerald-200">
              Simulation UI: Running
            </span>
          )}
          {!state.backendUiEnabled && (
            <span className="rounded-full bg-amber-500/20 px-3 py-1 text-amber-200">
              Desktop UI: Disabled
            </span>
          )}
          <button
            type="button"
            className="rounded-full bg-slate-700 px-3 py-1 text-slate-100 hover:bg-slate-600 disabled:opacity-60"
            onClick={handleRefresh}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
        {backendUiMessage && (
          <p className="mt-3 text-sm text-emerald-300">{backendUiMessage}</p>
        )}
        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      </header>

      {isAdmin && (
        <section className="mb-5 grid gap-2 rounded-2xl border border-white/10 bg-slate-900/60 p-3 sm:grid-cols-2 lg:grid-cols-4">
          {ADMIN_MENU.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setMenuId(item.id)}
              className={`rounded-lg px-3 py-2 text-sm ${menuId === item.id ? "bg-cyan-500 text-slate-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}
            >
              {item.label}
            </button>
          ))}
        </section>
      )}

      {state.emergency.active && (
        <section className="mb-6 animate-pulse rounded-2xl border border-rose-300/50 bg-rose-500/20 p-4">
          <p className="title-font text-sm uppercase tracking-[0.22em] text-rose-200">
            Emergency Mode Active
          </p>
          <p className="mt-1 text-base text-rose-50">
            Priority lane: <strong>{state.emergency.side || "N/A"}</strong> |
            Queue: <strong>{state.emergency.queue}</strong>
          </p>
        </section>
      )}

      {(!isAdmin || menuId === "live") && (
        <>
          <section className="grid gap-5 lg:grid-cols-[1fr_390px]">
            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur-sm">
              <IntersectionCanvas
                signals={state.signals}
                vehicleCounts={state.vehicleCounts}
                canControl={canControl}
                onManualOverride={(side) =>
                  callControl("/control/manual-override", { side })
                }
              />
            </div>

            <aside className="space-y-5">
              <div className="grid grid-cols-2 gap-3">
                {kpis.map((item) => (
                  <article
                    key={item.label}
                    className="rounded-2xl border border-cyan-300/15 bg-slate-900/70 p-3"
                  >
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      {item.label}
                    </p>
                    <p className="title-font mt-1 text-2xl text-cyan-200">
                      {item.value}
                    </p>
                  </article>
                ))}
              </div>

              <ControlPanel
                state={state}
                disabled={!canControl || loading}
                onToggleRunning={() =>
                  callControl("/control/running", { running: !state.running })
                }
                onReset={() => callControl("/control/reset")}
                onTriggerEmergency={(side) =>
                  callControl("/control/emergency", { side, duration: 12 })
                }
                onSpeedChange={(speed) =>
                  callControl("/control/speed", { speed })
                }
                onDurationsChange={(greenDuration, yellowDuration) =>
                  callControl("/control/timings", {
                    greenDuration,
                    yellowDuration,
                  })
                }
              />
            </aside>
          </section>

          <section className="mt-5 grid gap-5 md:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
              <h2 className="title-font text-lg text-slate-100">
                Side-Wise Queue and Signal State
              </h2>
              <div className="mt-4 space-y-3">
                {SIDES.map((side) => (
                  <div
                    key={side}
                    className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <p className="title-font text-sm text-slate-200">
                        {side}
                      </p>
                      <span className="rounded-full border border-slate-600 px-2 py-1 text-xs text-slate-300">
                        Queue: {state.vehicleCounts?.[side] ?? 0}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span
                        className={`h-3 w-3 rounded-full shadow-lg ${SIGNAL_COLORS[state.signals?.[side] || "RED"]}`}
                      />
                      <span className="text-xs uppercase tracking-[0.18em] text-slate-300">
                        {state.signals?.[side] || "RED"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
              <h2 className="title-font text-lg text-slate-100">
                Crossed Vehicle Analytics
              </h2>
              <div className="mt-4 space-y-3">
                <MetricRow
                  label="Cars"
                  value={state.crossedByType?.CAR || 0}
                  color="bg-cyan-400"
                />
                <MetricRow
                  label="Trucks"
                  value={state.crossedByType?.TRUCK || 0}
                  color="bg-orange-400"
                />
                <MetricRow
                  label="Ambulances"
                  value={state.crossedByType?.AMBULANCE || 0}
                  color="bg-rose-400"
                />
              </div>

              <h3 className="title-font mt-6 text-base text-slate-100">
                Runtime Events
              </h3>
              <ul className="mt-2 space-y-2 text-sm text-slate-300">
                {(state.events || []).map((event, idx) => (
                  <li
                    key={`${idx}-${event}`}
                    className="rounded-lg border border-slate-700/60 bg-slate-900/80 px-3 py-2"
                  >
                    {event}
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </>
      )}

      {isAdmin && menuId === "health" && (
        <SystemHealthPanel health={systemHealth} />
      )}
      {isAdmin && menuId === "audit" && <AuditTrailPanel logs={auditTrail} />}
      {isAdmin && menuId === "violations" && (
        <ViolationsPanel
          report={violations}
          onRefresh={loadAdminPanels}
          token={token}
        />
      )}
    </main>
  );
}

function LoginScreen({ onLoginSuccess }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("officer");
  const [password, setPassword] = useState("officer123");
  const [displayName, setDisplayName] = useState("Traffic Officer");
  const [signupRole, setSignupRole] = useState("officer");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = await fetchJson(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      onLoginSuccess(payload.token, payload.user);
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = await fetchJson(`${API_BASE}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
          displayName,
          role: signupRole,
        }),
      });

      onLoginSuccess(payload.token, payload.user);
    } catch (err) {
      setError(err.message || "Signup failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl items-center px-4 py-6 text-slate-100 sm:px-6">
      <section className="w-full rounded-3xl border border-cyan-300/20 bg-slate-900/70 p-6 backdrop-blur-sm">
        <p className="title-font text-xs uppercase tracking-[0.3em] text-cyan-300">
          Secure Access
        </p>
        <h1 className="title-font mt-2 text-3xl font-bold text-slate-50">
          Smart Traffic {mode === "login" ? "Login" : "Signup"}
        </h1>
        <p className="mt-2 text-sm text-slate-300">
          {mode === "login"
            ? "Sign in with your role-based account to continue."
            : "Create a new account in MySQL with admin/officer/viewer role."}
        </p>

        <div className="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`rounded-lg px-3 py-2 text-sm ${mode === "login" ? "bg-cyan-500 text-slate-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("signup")}
            className={`rounded-lg px-3 py-2 text-sm ${mode === "signup" ? "bg-cyan-500 text-slate-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}
          >
            Signup
          </button>
        </div>

        {mode === "login" ? (
          <form className="mt-5 space-y-4" onSubmit={handleLogin}>
            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                required
              />
            </div>

            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Login"}
            </button>
          </form>
        ) : (
          <form className="mt-5 space-y-4" onSubmit={handleSignup}>
            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Display Name
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                required
              />
            </div>

            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                required
              />
            </div>

            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
                required
                minLength={6}
              />
            </div>

            <div>
              <label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                Role
              </label>
              <select
                value={signupRole}
                onChange={(event) => setSignupRole(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              >
                <option value="admin">Admin</option>
                <option value="officer">Officer</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
            >
              {loading ? "Creating account..." : "Signup"}
            </button>
          </form>
        )}

        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}

        <div className="mt-5 rounded-lg border border-slate-700 bg-slate-900/70 p-3 text-xs text-slate-300">
          <p className="font-semibold text-slate-200">Seeded Accounts</p>
          <p>officer / officer123</p>
          <p>admin / admin123</p>
          <p>viewer / viewer123</p>
        </div>
      </section>
    </main>
  );
}

function ControlPanel({
  state,
  disabled,
  onToggleRunning,
  onReset,
  onTriggerEmergency,
  onSpeedChange,
  onDurationsChange,
}) {
  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/70 p-4">
      <h2 className="title-font text-lg text-slate-100">
        Traffic Personnel Controls
      </h2>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <button
          type="button"
          disabled={disabled}
          className="rounded-xl bg-cyan-500 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-cyan-400 disabled:opacity-60"
          onClick={onToggleRunning}
        >
          {state.running ? "Pause" : "Resume"}
        </button>
        <button
          type="button"
          disabled={disabled}
          className="rounded-xl bg-slate-700 px-3 py-2 text-sm font-semibold text-slate-100 hover:bg-slate-600 disabled:opacity-60"
          onClick={onReset}
        >
          Reset
        </button>
      </div>

      <label className="mt-4 block text-xs uppercase tracking-[0.18em] text-slate-400">
        Simulation Speed ({state.speed.toFixed(1)}x)
      </label>
      <input
        type="range"
        min="0.2"
        max="3"
        step="0.1"
        defaultValue={state.speed}
        className="mt-2 w-full accent-cyan-400"
        disabled={disabled}
        onMouseUp={(event) => onSpeedChange(Number(event.currentTarget.value))}
        onTouchEnd={(event) => onSpeedChange(Number(event.currentTarget.value))}
      />

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Green (s)
          </label>
          <input
            type="number"
            min="5"
            max="40"
            defaultValue={state.greenDuration}
            disabled={disabled}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
            onBlur={(event) =>
              onDurationsChange(
                Number(event.target.value),
                state.yellowDuration,
              )
            }
          />
        </div>
        <div>
          <label className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Yellow (s)
          </label>
          <input
            type="number"
            min="2"
            max="10"
            defaultValue={state.yellowDuration}
            disabled={disabled}
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
            onBlur={(event) =>
              onDurationsChange(state.greenDuration, Number(event.target.value))
            }
          />
        </div>
      </div>

      <p className="mt-4 text-xs uppercase tracking-[0.18em] text-slate-400">
        Trigger Emergency
      </p>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {SIDES.map((side) => (
          <button
            key={`em-${side}`}
            type="button"
            disabled={disabled}
            className="rounded-lg border border-rose-400/40 bg-rose-500/10 px-2 py-2 text-xs text-rose-100 hover:bg-rose-500/20 disabled:opacity-60"
            onClick={() => onTriggerEmergency(side)}
          >
            {side}
          </button>
        ))}
      </div>
    </section>
  );
}

function IntersectionCanvas({
  signals,
  vehicleCounts,
  canControl,
  onManualOverride,
}) {
  const sidesWithPosition = {
    NORTH: "left-1/2 top-4 -translate-x-1/2",
    SOUTH: "left-1/2 bottom-4 -translate-x-1/2",
    EAST: "right-4 top-1/2 -translate-y-1/2",
    WEST: "left-4 top-1/2 -translate-y-1/2",
  };

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[700px] overflow-hidden rounded-3xl border border-slate-700/60 bg-slate-950">
      <div className="absolute inset-y-0 left-1/2 w-48 -translate-x-1/2 bg-slate-800" />
      <div className="absolute inset-x-0 top-1/2 h-48 -translate-y-1/2 bg-slate-800" />
      <div className="absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-xl border-2 border-dashed border-cyan-300/50 bg-cyan-500/10" />

      {SIDES.map((side) => (
        <div key={side} className={`absolute ${sidesWithPosition[side]}`}>
          <button
            type="button"
            disabled={!canControl}
            onClick={() => onManualOverride(side)}
            className="rounded-xl border border-slate-600/60 bg-slate-900/85 px-3 py-2 text-left hover:border-cyan-300/60 disabled:cursor-default"
          >
            <div className="flex items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full shadow-md ${SIGNAL_COLORS[signals?.[side] || "RED"]}`}
              />
              <span className="title-font text-xs text-slate-200">{side}</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">
              Vehicles: {vehicleCounts?.[side] || 0}
            </p>
            {canControl && (
              <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-cyan-300">
                Click To Manual Green
              </p>
            )}
          </button>
        </div>
      ))}

      <div className="absolute bottom-3 left-3 rounded-lg border border-cyan-300/20 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100">
        Direct Manipulation Intersection
      </div>
    </div>
  );
}

function MetricRow({ label, value, color }) {
  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-200">{label}</span>
        <span className="title-font text-slate-100">{value}</span>
      </div>
      <div className="mt-2 h-2 rounded-full bg-slate-700/60">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${Math.min(100, value * 6)}%` }}
        />
      </div>
    </div>
  );
}

function SystemHealthPanel({ health }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
      <h2 className="title-font text-lg text-slate-100">System Health</h2>
      {!health && (
        <p className="mt-3 text-slate-300">Loading health metrics...</p>
      )}
      {health && (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {Object.entries(health).map(([key, value]) => (
            <article
              key={key}
              className="rounded-xl border border-slate-700/60 bg-slate-900/80 p-3"
            >
              <p className="text-xs uppercase tracking-[0.16em] text-slate-400">
                {key}
              </p>
              <p className="mt-1 text-sm text-slate-100">{String(value)}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function AuditTrailPanel({ logs }) {
  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
      <h2 className="title-font text-lg text-slate-100">Audit Trail</h2>
      <ul className="mt-4 space-y-2">
        {logs.length === 0 && (
          <li className="text-slate-300">No audit entries yet.</li>
        )}
        {logs.map((entry, idx) => (
          <li
            key={`${entry.timestamp}-${idx}`}
            className="rounded-lg border border-slate-700/60 bg-slate-900/80 p-3 text-sm"
          >
            <p className="text-slate-200">
              <strong>{entry.action}</strong> by {entry.actor} ({entry.role})
            </p>
            <p className="text-slate-400">{entry.details}</p>
            <p className="text-xs text-slate-500">
              {new Date(entry.timestamp * 1000).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ViolationsPanel({ report, onRefresh, token }) {
  const rows = report?.rows || [];
  const [busyId, setBusyId] = useState(null);
  const [panelMessage, setPanelMessage] = useState("");
  const [panelError, setPanelError] = useState("");
  const [sortBy, setSortBy] = useState("time_desc");

  const sortedRows = useMemo(() => {
    const getTimeValue = (value) => {
      if (!value) {
        return 0;
      }
      const parsed = new Date(value).getTime();
      return Number.isNaN(parsed) ? 0 : parsed;
    };

    const compareText = (a, b) =>
      String(a || "").localeCompare(String(b || ""));
    const compareBool = (a, b) => Number(Boolean(a)) - Number(Boolean(b));

    const sorted = [...rows].sort((a, b) => {
      switch (sortBy) {
        case "time_asc":
          return getTimeValue(a.createdAt) - getTimeValue(b.createdAt);
        case "time_desc":
          return getTimeValue(b.createdAt) - getTimeValue(a.createdAt);
        case "name_asc":
          return compareText(a.vehicleId, b.vehicleId);
        case "name_desc":
          return compareText(b.vehicleId, a.vehicleId);
        case "action_taken_first": {
          const takenOrder = compareBool(b.actionTaken, a.actionTaken);
          if (takenOrder !== 0) {
            return takenOrder;
          }
          return getTimeValue(b.createdAt) - getTimeValue(a.createdAt);
        }
        case "action_not_taken_first": {
          const notTakenOrder = compareBool(a.actionTaken, b.actionTaken);
          if (notTakenOrder !== 0) {
            return notTakenOrder;
          }
          return getTimeValue(b.createdAt) - getTimeValue(a.createdAt);
        }
        case "type_asc":
          return compareText(a.vehicleType, b.vehicleType);
        case "side_asc":
          return compareText(a.side, b.side);
        case "violation_asc":
          return compareText(a.violationType, b.violationType);
        case "id_desc":
          return Number(b.id || 0) - Number(a.id || 0);
        case "id_asc":
          return Number(a.id || 0) - Number(b.id || 0);
        default:
          return 0;
      }
    });

    return sorted;
  }, [rows, sortBy]);

  const updateActionStatus = async (violationId, nextValue) => {
    setBusyId(violationId);
    setPanelMessage("");
    setPanelError("");

    try {
      await fetchJson(`${API_BASE}/violations/${violationId}/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ actionTaken: nextValue === "taken" }),
      });
      await onRefresh();
      setPanelMessage(`Violation ${violationId} action updated.`);
    } catch (err) {
      setPanelError(err.message || "Failed to update action status.");
    } finally {
      setBusyId(null);
    }
  };

  const deleteViolation = async (violationId) => {
    setBusyId(violationId);
    setPanelMessage("");
    setPanelError("");

    try {
      await fetchJson(`${API_BASE}/violations/${violationId}/delete`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      await onRefresh();
      setPanelMessage(`Violation ${violationId} deleted.`);
    } catch (err) {
      setPanelError(err.message || "Failed to delete violation.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="title-font text-lg text-slate-100">Violation Reports</h2>
        <div className="flex items-center gap-2">
          <label className="text-[11px] uppercase tracking-[0.16em] text-slate-300">
            Sort By
          </label>
          <select
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-100"
          >
            <option value="time_desc">Time (Newest First)</option>
            <option value="time_asc">Time (Oldest First)</option>
            <option value="name_asc">Name (A-Z)</option>
            <option value="name_desc">Name (Z-A)</option>
            <option value="action_taken_first">Action (Taken First)</option>
            <option value="action_not_taken_first">
              Action (Not Taken First)
            </option>
            <option value="type_asc">Vehicle Type</option>
            <option value="side_asc">Side</option>
            <option value="violation_asc">Violation Type</option>
            <option value="id_desc">ID (High-Low)</option>
            <option value="id_asc">ID (Low-High)</option>
          </select>
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-lg bg-slate-700 px-3 py-1 text-xs uppercase tracking-[0.16em] text-slate-100 hover:bg-slate-600"
          >
            Refresh Report
          </button>
        </div>
      </div>

      {panelMessage && (
        <p className="mt-3 text-sm text-emerald-300">{panelMessage}</p>
      )}
      {panelError && <p className="mt-3 text-sm text-rose-300">{panelError}</p>}

      {!report && <p className="mt-3 text-slate-300">Loading report data...</p>}

      {report && (
        <>
          <div className="mt-4 space-y-1 text-sm text-slate-300">
            <p>
              Status:{" "}
              <strong className="text-slate-100">{report.status}</strong>
            </p>
            <p>{report.message}</p>
            <p>
              Total Rows:{" "}
              <strong className="text-slate-100">{report.total}</strong>
            </p>
          </div>

          {rows.length === 0 ? (
            <p className="mt-4 text-sm text-slate-300">
              No violation rows found in MySQL table.
            </p>
          ) : (
            <div className="mt-4 overflow-x-auto rounded-xl border border-slate-700/60">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-800/70 text-xs uppercase tracking-[0.12em] text-slate-300">
                  <tr>
                    <th className="px-3 py-2">ID</th>
                    <th className="px-3 py-2">Vehicle</th>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Side</th>
                    <th className="px-3 py-2">Violation</th>
                    <th className="px-3 py-2">In Middle</th>
                    <th className="px-3 py-2">Out Middle</th>
                    <th className="px-3 py-2">Action Taken</th>
                    <th className="px-3 py-2">Created At</th>
                    <th className="px-3 py-2">Delete</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedRows.map((row) => {
                    const isTaken = Boolean(row.actionTaken);
                    const rowBusy = busyId === row.id;

                    return (
                      <tr
                        key={row.id}
                        className="border-t border-slate-700/60 bg-slate-900/70 text-slate-200"
                      >
                        <td className="px-3 py-2">{row.id}</td>
                        <td className="px-3 py-2">{row.vehicleId}</td>
                        <td className="px-3 py-2">{row.vehicleType}</td>
                        <td className="px-3 py-2">{row.side}</td>
                        <td className="px-3 py-2">{row.violationType}</td>
                        <td className="px-3 py-2">
                          {row.inMiddle ? "Yes" : "No"}
                        </td>
                        <td className="px-3 py-2">
                          {row.outMiddle ? "Yes" : "No"}
                        </td>
                        <td className="px-3 py-2">
                          <select
                            value={isTaken ? "taken" : "not_taken"}
                            disabled={rowBusy}
                            className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs"
                            onChange={(event) =>
                              updateActionStatus(row.id, event.target.value)
                            }
                          >
                            <option value="not_taken">Not Taken</option>
                            <option value="taken">Taken</option>
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          {row.createdAt
                            ? new Date(row.createdAt).toLocaleString()
                            : "-"}
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            disabled={rowBusy || !isTaken}
                            onClick={() => deleteViolation(row.id)}
                            className="rounded-md bg-rose-500/20 px-2 py-1 text-xs text-rose-200 hover:bg-rose-500/30 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default App;
