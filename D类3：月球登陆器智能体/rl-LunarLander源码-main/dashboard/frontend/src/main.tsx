import React from "react";
import { createRoot } from "react-dom/client";
import {
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  Pause,
  Play,
  RefreshCcw,
  Rocket,
  Settings2,
  TerminalSquare
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import "./styles.css";

type EnvMode = "base" | "real";
type DeviceMode = "cpu" | "cuda";
type ViewMode = "train" | "evaluate";
type JobStatus = "pending" | "running" | "done" | "failed";

type RunSummary = {
  id: string;
  env_mode: EnvMode;
  exp_id: number;
  name: string;
  has_final_model: boolean;
  has_best_model: boolean;
  has_evaluations: boolean;
  model_name: string | null;
  best_model_name: string | null;
  latest_mean_reward: number | null;
  latest_mean_length: number | null;
  latest_timestep: number | null;
};

type MetricPoint = {
  timestep: number;
  mean_reward: number;
  std_reward: number | null;
  mean_length: number | null;
};

type RunMetrics = {
  points: MetricPoint[];
  summary: Record<string, number | string | null>;
};

type Job = {
  id: string;
  kind: "train" | "evaluate";
  status: JobStatus;
  env_mode: EnvMode;
  output: string;
  result: Record<string, string | number> | null;
};

type ReplayState = {
  frame: string | null;
  step: number;
  action: number | null;
  reward: number;
  episodeReward: number;
  status: "idle" | "playing" | "done" | "error";
  message: string;
};

const api = {
  runs: (): Promise<RunSummary[]> => fetch("/api/runs").then((res) => res.json()),
  jobs: (): Promise<Job[]> => fetch("/api/jobs").then((res) => res.json()),
  metrics: (run: RunSummary): Promise<RunMetrics> =>
    fetch(`/api/metrics/${run.env_mode}/${run.exp_id}`).then((res) => res.json()),
  train: (payload: { env_mode: EnvMode; timesteps: number; n_envs: number; device: string }) =>
    fetch("/api/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json()),
  evaluate: (payload: { env_mode: EnvMode; exp_id?: number; episodes: number; use_best: boolean; device: string }) =>
    fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json())
};

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return value.toFixed(digits);
}

function latestRun(runs: RunSummary[], env: EnvMode) {
  return runs.filter((run) => run.env_mode === env).sort((a, b) => b.exp_id - a.exp_id)[0] ?? null;
}

function App() {
  const [view, setView] = React.useState<ViewMode>("train");
  const [runs, setRuns] = React.useState<RunSummary[]>([]);
  const [jobs, setJobs] = React.useState<Job[]>([]);
  const [trainEnv, setTrainEnv] = React.useState<EnvMode>("base");
  const [evalEnv, setEvalEnv] = React.useState<EnvMode>("base");
  const [trainDevice, setTrainDevice] = React.useState<DeviceMode>("cpu");
  const [evalDevice, setEvalDevice] = React.useState<DeviceMode>("cpu");
  const [selectedRunId, setSelectedRunId] = React.useState<string>("");
  const [metrics, setMetrics] = React.useState<RunMetrics | null>(null);
  const [timesteps, setTimesteps] = React.useState(256);
  const [nEnvs, setNEnvs] = React.useState(1);
  const [episodes, setEpisodes] = React.useState(20);
  const [useBest, setUseBest] = React.useState(true);
  const [replay, setReplay] = React.useState<ReplayState>({
    frame: null,
    step: 0,
    action: null,
    reward: 0,
    episodeReward: 0,
    status: "idle",
    message: "Ready"
  });
  const socketRef = React.useRef<WebSocket | null>(null);

  const visibleRuns = React.useMemo(() => runs.filter((run) => run.env_mode === evalEnv), [runs, evalEnv]);
  const selectedRun = React.useMemo(
    () => visibleRuns.find((run) => run.id === selectedRunId) ?? null,
    [visibleRuns, selectedRunId]
  );
  const trainReferenceRun = latestRun(runs, trainEnv);
  const activeTrainJob = jobs.find((job) => job.kind === "train" && (job.status === "running" || job.status === "pending"));
  const activeEvalJob = jobs.find((job) => job.kind === "evaluate" && (job.status === "running" || job.status === "pending"));

  const refresh = React.useCallback(async () => {
    const [nextRuns, nextJobs] = await Promise.all([api.runs(), api.jobs()]);
    setRuns(nextRuns);
    setJobs(nextJobs);
    if (!selectedRunId) {
      const nextSelected = latestRun(nextRuns, evalEnv);
      if (nextSelected) setSelectedRunId(nextSelected.id);
    }
  }, [evalEnv, selectedRunId]);

  React.useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 3000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  React.useEffect(() => {
    if (!selectedRun) {
      setMetrics(null);
      return;
    }
    api.metrics(selectedRun).then(setMetrics).catch(() => setMetrics(null));
  }, [selectedRun]);

  React.useEffect(() => {
    if (visibleRuns.length === 0) {
      if (selectedRunId) setSelectedRunId("");
      return;
    }
    if (!visibleRuns.some((run) => run.id === selectedRunId)) {
      setSelectedRunId(visibleRuns[0].id);
    }
  }, [visibleRuns, selectedRunId]);

  async function launchTrain() {
    const ok = window.confirm(
      `确认启动 ${trainEnv.toUpperCase()} 环境训练？\n设备: ${trainDevice.toUpperCase()}\n训练轮数: ${timesteps}\n并行环境数: ${nEnvs}`
    );
    if (!ok) return;
    await api.train({ env_mode: trainEnv, timesteps, n_envs: nEnvs, device: trainDevice });
    await refresh();
  }

  async function launchEvaluate() {
    if (!selectedRun) return;
    const ok = window.confirm(
      `确认测评模型 ${selectedRun.name}？\n环境: ${selectedRun.env_mode.toUpperCase()}\n设备: ${evalDevice.toUpperCase()}\n测评回合数: ${episodes}`
    );
    if (!ok) return;
    await api.evaluate({
      env_mode: selectedRun.env_mode,
      exp_id: selectedRun.exp_id,
      episodes,
      use_best: useBest,
      device: evalDevice
    });
    await refresh();
    startReplayForRun(selectedRun);
  }

  function startReplay() {
    if (!selectedRun) return;
    startReplayForRun(selectedRun);
  }

  function startReplayForRun(run: RunSummary) {
    socketRef.current?.close();
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const query = new URLSearchParams({
      use_best: String(useBest && run.has_best_model),
      device: evalDevice,
      max_steps: "1000",
      delay_ms: "90"
    });
    const socket = new WebSocket(
      `${protocol}://${window.location.host}/api/replay/${run.env_mode}/${run.exp_id}?${query}`
    );
    socketRef.current = socket;
    setReplay((prev) => ({ ...prev, status: "playing", message: "Streaming replay" }));
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "frame") {
        setReplay({
          frame: payload.frame,
          step: payload.step,
          action: payload.action,
          reward: payload.reward,
          episodeReward: payload.episode_reward,
          status: payload.done ? "done" : "playing",
          message: payload.done ? "Episode complete" : "Streaming replay"
        });
      } else if (payload.type === "done") {
        setReplay((prev) => ({ ...prev, status: "done", message: "Episode complete" }));
      } else if (payload.type === "error") {
        setReplay((prev) => ({ ...prev, status: "error", message: payload.message }));
      }
    };
    socket.onclose = () => {
      setReplay((prev) => (prev.status === "playing" ? { ...prev, status: "idle", message: "Stopped" } : prev));
    };
  }

  function stopReplay() {
    socketRef.current?.close();
    socketRef.current = null;
    setReplay((prev) => ({ ...prev, status: "idle", message: "Paused" }));
  }

  function selectRun(runId: string) {
    if (runId === selectedRunId) return;
    socketRef.current?.close();
    socketRef.current = null;
    setReplay({
      frame: null,
      step: 0,
      action: null,
      reward: 0,
      episodeReward: 0,
      status: "idle",
      message: "Ready"
    });
    setSelectedRunId(runId);
  }

  return (
    <main className="app">
      <header className="header">
        <div className="brandLine">
          <Rocket size={25} />
          <div>
            <strong>LunarLander PPO</strong>
            <span>Training and evaluation console</span>
          </div>
        </div>
        <div className="viewTabs">
          <button className={view === "train" ? "active" : ""} onClick={() => setView("train")}>
            <TerminalSquare size={18} />
            训练
          </button>
          <button className={view === "evaluate" ? "active" : ""} onClick={() => setView("evaluate")}>
            <ClipboardCheck size={18} />
            测评
          </button>
        </div>
        <button className="iconButton" onClick={refresh} aria-label="Refresh">
          <RefreshCcw size={18} />
        </button>
      </header>

      {view === "train" ? (
        <TrainView
          env={trainEnv}
          setEnv={setTrainEnv}
          timesteps={timesteps}
          setTimesteps={setTimesteps}
          nEnvs={nEnvs}
          setNEnvs={setNEnvs}
          device={trainDevice}
          setDevice={setTrainDevice}
          onTrain={launchTrain}
          job={activeTrainJob}
          run={trainReferenceRun}
          metrics={trainReferenceRun?.id === selectedRun?.id ? metrics : null}
        />
      ) : (
        <EvaluateView
          evalEnv={evalEnv}
          setEvalEnv={setEvalEnv}
          runs={visibleRuns}
          selectedRun={selectedRun}
          selectRun={selectRun}
          metrics={metrics}
          episodes={episodes}
          setEpisodes={setEpisodes}
          useBest={useBest}
          setUseBest={setUseBest}
          device={evalDevice}
          setDevice={setEvalDevice}
          onEvaluate={launchEvaluate}
          evalJob={activeEvalJob}
          replay={replay}
          startReplay={startReplay}
          stopReplay={stopReplay}
        />
      )}
    </main>
  );
}

function TrainView({
  env,
  setEnv,
  timesteps,
  setTimesteps,
  nEnvs,
  setNEnvs,
  device,
  setDevice,
  onTrain,
  job,
  run,
  metrics
}: {
  env: EnvMode;
  setEnv: (env: EnvMode) => void;
  timesteps: number;
  setTimesteps: (value: number) => void;
  nEnvs: number;
  setNEnvs: (value: number) => void;
  device: DeviceMode;
  setDevice: (value: DeviceMode) => void;
  onTrain: () => void;
  job?: Job;
  run: RunSummary | null;
  metrics: RunMetrics | null;
}) {
  const points = metrics?.points ?? [];
  return (
    <section className="page trainPage">
      <aside className="controlPanel">
        <p className="eyebrow">Train</p>
        <h1>训练监控</h1>
        <div className="envSelector">
          <button className={env === "base" ? "active" : ""} onClick={() => setEnv("base")}>Base</button>
          <button className={env === "real" ? "active" : ""} onClick={() => setEnv("real")}>Real</button>
        </div>
        <label>
          训练轮数
          <input type="number" min={1} value={timesteps} onChange={(event) => setTimesteps(Number(event.target.value))} />
        </label>
        <label>
          并行环境数
          <input type="number" min={1} value={nEnvs} onChange={(event) => setNEnvs(Number(event.target.value))} />
        </label>
        <DeviceSelector value={device} onChange={setDevice} />
        <button className="primaryAction" onClick={onTrain}>
          <TerminalSquare size={18} />
          开启训练
        </button>
        <div className={`statusBox ${job?.status ?? "idle"}`}>
          <span>当前训练环境</span>
          <strong>{env.toUpperCase()}</strong>
          <span>训练状态</span>
          <strong>{job?.status ?? "idle"}</strong>
          <span>计算设备</span>
          <strong>{device.toUpperCase()}</strong>
        </div>
      </aside>

      <section className="monitorPanel">
        <div className="panelTitle">
          <div>
            <h2>训练曲线监控</h2>
            <p>{run ? `${run.name} · latest reward ${formatNumber(run.latest_mean_reward)}` : "No run detected"}</p>
          </div>
          <BarChart3 size={22} />
        </div>
        <ResponsiveContainer width="100%" height={430}>
          <AreaChart data={points}>
            <CartesianGrid stroke="#d9e0e8" strokeDasharray="3 3" />
            <XAxis dataKey="timestep" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Area type="monotone" dataKey="mean_reward" stroke="#1d4ed8" fill="#bfdbfe" />
          </AreaChart>
        </ResponsiveContainer>
        <div className="metricGrid">
          <Stat label="Latest reward" value={formatNumber(run?.latest_mean_reward)} />
          <Stat label="Mean length" value={formatNumber(run?.latest_mean_length)} />
          <Stat label="Timestep" value={run?.latest_timestep ? String(run.latest_timestep) : "-"} />
        </div>
      </section>
    </section>
  );
}

function EvaluateView({
  evalEnv,
  setEvalEnv,
  runs,
  selectedRun,
  selectRun,
  metrics,
  episodes,
  setEpisodes,
  useBest,
  setUseBest,
  device,
  setDevice,
  onEvaluate,
  evalJob,
  replay,
  startReplay,
  stopReplay
}: {
  evalEnv: EnvMode;
  setEvalEnv: (env: EnvMode) => void;
  runs: RunSummary[];
  selectedRun: RunSummary | null;
  selectRun: (id: string) => void;
  metrics: RunMetrics | null;
  episodes: number;
  setEpisodes: (value: number) => void;
  useBest: boolean;
  setUseBest: (value: boolean) => void;
  device: DeviceMode;
  setDevice: (value: DeviceMode) => void;
  onEvaluate: () => void;
  evalJob?: Job;
  replay: ReplayState;
  startReplay: () => void;
  stopReplay: () => void;
}) {
  return (
    <section className="page evaluatePage">
      <section className="replayHero">
        <div className="panelTitle">
          <div>
            <h1>测评回放</h1>
            <p>{selectedRun ? `${selectedRun.name} · ${replay.message}` : "No model selected"}</p>
          </div>
          <div className="replayControls">
            <button className="iconButton" onClick={startReplay} disabled={!selectedRun || replay.status === "playing"}>
              <Play size={18} />
            </button>
            <button className="iconButton" onClick={stopReplay}>
              <Pause size={18} />
            </button>
          </div>
        </div>
        <div className="largeReplay">
          {replay.frame ? <img src={replay.frame} alt="LunarLander rollout frame" /> : <Rocket size={82} />}
        </div>
        <div className="metricGrid">
          <Stat label="Step" value={String(replay.step)} />
          <Stat label="Action" value={replay.action === null ? "-" : String(replay.action)} />
          <Stat label="Reward" value={formatNumber(replay.reward, 3)} />
          <Stat label="Return" value={formatNumber(replay.episodeReward, 2)} />
        </div>
      </section>

      <aside className="evalSide">
        <article className="card">
          <div className="panelTitle compact">
            <div>
              <h2>自动识别模型</h2>
              <p>{runs.length} models in {evalEnv}</p>
            </div>
            <CheckCircle2 size={20} />
          </div>
          <div className="envSelector">
            <button className={evalEnv === "base" ? "active" : ""} onClick={() => setEvalEnv("base")}>Base</button>
            <button className={evalEnv === "real" ? "active" : ""} onClick={() => setEvalEnv("real")}>Real</button>
          </div>
          <DeviceSelector value={device} onChange={setDevice} />
          <div className="modelList">
            {runs.map((run) => (
              <button
                className={selectedRun?.id === run.id ? "modelRow active" : "modelRow"}
                key={run.id}
                onClick={() => selectRun(run.id)}
              >
                <strong>{run.name}</strong>
                <span>{run.has_best_model && useBest ? run.best_model_name : run.model_name}</span>
                <em>reward {formatNumber(run.latest_mean_reward)}</em>
              </button>
            ))}
          </div>
        </article>

        <article className="card">
          <div className="panelTitle compact">
            <div>
              <h2>测评参数</h2>
              <p>{evalJob?.status ?? "idle"}</p>
            </div>
            <Settings2 size={20} />
          </div>
          <label>
            测评回合数
            <input type="number" min={1} value={episodes} onChange={(event) => setEpisodes(Number(event.target.value))} />
          </label>
          <label className="toggle">
            <input type="checkbox" checked={useBest} onChange={(event) => setUseBest(event.target.checked)} />
            优先使用 best_model.zip
          </label>
          <button className="primaryAction" onClick={onEvaluate} disabled={!selectedRun}>
            <ClipboardCheck size={18} />
            开启测评
          </button>
        </article>

        <article className="card curveCard">
          <div className="panelTitle compact">
            <div>
              <h2>测评曲线</h2>
              <p>{selectedRun?.name ?? "No run"}</p>
            </div>
            <BarChart3 size={20} />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={metrics?.points ?? []}>
              <CartesianGrid stroke="#d9e0e8" strokeDasharray="3 3" />
              <XAxis dataKey="timestep" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="mean_reward" stroke="#0f766e" fill="#ccfbf1" />
            </AreaChart>
          </ResponsiveContainer>
        </article>
      </aside>
    </section>
  );
}

function DeviceSelector({ value, onChange }: { value: DeviceMode; onChange: (value: DeviceMode) => void }) {
  return (
    <div className="deviceSelector" aria-label="Device selector">
      <span>计算设备</span>
      <div>
        <button className={value === "cpu" ? "active" : ""} onClick={() => onChange("cpu")}>CPU</button>
        <button className={value === "cuda" ? "active" : ""} onClick={() => onChange("cuda")}>GPU</button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
