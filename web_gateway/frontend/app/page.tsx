'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';

type JointState = {
  names: string[];
  positions: number[];
  received_at: string | null;
};

type Recording = {
  id: string;
  status: 'recording' | 'ready';
  started_at: string;
  stopped_at: string | null;
  size_bytes: number;
};

type Task = {
  id: string;
  target_degrees: number;
  status: string;
  progress: number;
  remaining_delta: number | null;
  created_at: string;
};

type LogEntry = {
  at: string;
  level: 'info' | 'warning' | 'error';
  message: string;
};

type Snapshot = {
  robot_online: boolean;
  ros_available: boolean;
  ros_reason: string | null;
  motors_enabled: boolean;
  joint_state: JointState;
  active_recording: Recording | null;
};

const gatewayUrl =
  process.env.NEXT_PUBLIC_GATEWAY_URL ?? 'http://localhost:8000';

function websocketUrl() {
  return gatewayUrl.replace(/^http/, 'ws') + '/ws/telemetry';
}

function formatTime(value: string | null) {
  if (!value) return '尚未收到';
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }).format(new Date(value));
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  return `${(value / 1024).toFixed(1)} KB`;
}

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [targetDegrees, setTargetDegrees] = useState('90');
  const [error, setError] = useState('');

  const request = useCallback(async <T,>(path: string, init?: RequestInit) => {
    const response = await fetch(`${gatewayUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ?? `Request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [nextSnapshot, nextTasks, nextRecordings, nextLogs] = await Promise.all([
        request<Snapshot>('/api/status'),
        request<Task[]>('/api/tasks'),
        request<Recording[]>('/api/recordings'),
        request<LogEntry[]>('/api/logs'),
      ]);
      setSnapshot(nextSnapshot);
      setTasks(nextTasks);
      setRecordings(nextRecordings);
      setLogs(nextLogs);
      setError('');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '连接失败');
    }
  }, [request]);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 3000);
    const socket = new WebSocket(websocketUrl());
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as {
        type: 'snapshot';
        payload: Snapshot;
      };
      if (message.type === 'snapshot') setSnapshot(message.payload);
    };
    return () => {
      window.clearInterval(timer);
      socket.close();
    };
  }, [refresh]);

  async function runAction(event: FormEvent) {
    event.preventDefault();
    try {
      await request<Task>('/api/tasks', {
        method: 'POST',
        body: JSON.stringify({ target_degrees: Number(targetDegrees) }),
      });
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '任务创建失败');
    }
  }

  async function setMotors(enabled: boolean) {
    try {
      await request('/api/motors', {
        method: 'POST', body: JSON.stringify({ enabled }),
      });
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '电机请求失败');
    }
  }

  async function cancelTask(taskId: string) {
    try {
      await request(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '取消失败');
    }
  }

  async function toggleRecording() {
    try {
      const path = snapshot?.active_recording
        ? '/api/recordings/stop' : '/api/recordings';
      await request(path, { method: 'POST' });
      await refresh();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '录制操作失败');
    }
  }

  const jointPairs = snapshot?.joint_state.names.map((name, index) => ({
    name, position: snapshot.joint_state.positions[index] ?? 0,
  })) ?? [];

  return (
    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">MONTH 01 · BUILD</p>
          <h1>ROS2 Web Gateway <span>v0.1</span></h1>
          <p className="subtitle">一次机器人运行的观察、控制与复盘台。</p>
        </div>
        <div className={snapshot?.robot_online ? 'badge online' : 'badge'}>
          <i /> {snapshot?.robot_online ? '机器人在线' : '等待机器人'}
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      <section className="grid overview">
        <article className="card status-card">
          <p className="label">ROS2 BRIDGE</p>
          <strong>{snapshot?.ros_available ? '已连接' : '未连接'}</strong>
          <p>{snapshot?.ros_reason ?? '正在接收 /joint_states'}</p>
        </article>
        <article className="card status-card">
          <p className="label">最后状态</p>
          <strong>{formatTime(snapshot?.joint_state.received_at ?? null)}</strong>
          <p>{jointPairs.length} 个关节数据正在被观察</p>
        </article>
        <article className="card status-card recording-card">
          <p className="label">MCAP 录制</p>
          <strong>{snapshot?.active_recording ? '录制中' : '未录制'}</strong>
          <button onClick={toggleRecording} disabled={!snapshot?.ros_available}>
            {snapshot?.active_recording ? '停止并保存' : '开始录制'}
          </button>
        </article>
      </section>

      <section className="grid primary-grid">
        <article className="card joints">
          <div className="card-heading">
            <div><p className="label">实时数据</p><h2>R2D2 关节状态</h2></div>
            <span className="topic">/joint_states</span>
          </div>
          {jointPairs.length ? jointPairs.map((joint) => (
            <div className="joint-row" key={joint.name}>
              <span>{joint.name}</span>
              <div><i style={{ width: `${Math.min(100, Math.abs(joint.position) * 200 + 8)}%` }} /></div>
              <b>{joint.position.toFixed(3)} rad</b>
            </div>
          )) : <p className="empty">等待演示节点发布关节数据。</p>}
        </article>

        <article className="card controls">
          <p className="label">受限控制</p>
          <h2>任务与电机</h2>
          <p className="muted">仅开放演示白名单，绝不转发任意 ROS 指令。</p>
          <div className="button-row">
            <button onClick={() => setMotors(true)} disabled={!snapshot?.ros_available}>
              启用电机
            </button>
            <button className="quiet" onClick={() => setMotors(false)} disabled={!snapshot?.ros_available}>
              停用电机
            </button>
          </div>
          <form onSubmit={runAction}>
            <label htmlFor="degrees">模拟机器人朝向（度）</label>
            <div className="input-row">
              <input id="degrees" value={targetDegrees} type="number" min="-180" max="180"
                onChange={(event) => setTargetDegrees(event.target.value)} />
              <button disabled={!snapshot?.ros_available}>创建任务</button>
            </div>
          </form>
        </article>
      </section>

      <section className="grid lower-grid">
        <article className="card">
          <div className="card-heading"><div><p className="label">ACTION</p><h2>任务进度</h2></div></div>
          {tasks.length ? tasks.slice(0, 4).map((task) => (
            <div className="task" key={task.id}>
              <div><b>{task.target_degrees}° 模拟转向</b><span>{task.status}</span></div>
              <div className="progress"><i style={{ width: `${task.progress}%` }} /></div>
              <small>{task.progress.toFixed(0)}% · {formatTime(task.created_at)}</small>
              {['queued', 'running', 'cancel_requested'].includes(task.status) && (
                <button className="text-button" onClick={() => cancelTask(task.id)}>取消</button>
              )}
            </div>
          )) : <p className="empty">还没有任务。</p>}
        </article>

        <article className="card">
          <div className="card-heading"><div><p className="label">MCAP</p><h2>运行记录</h2></div></div>
          {recordings.length ? recordings.slice(0, 4).map((recording) => (
            <div className="recording" key={recording.id}>
              <b>{recording.id}</b><span>{recording.status === 'recording' ? '写入中' : formatBytes(recording.size_bytes)}</span>
            </div>
          )) : <p className="empty">尚无录制。开始一次实验即可生成记录。</p>}
        </article>

        <article className="card logs">
          <div className="card-heading"><div><p className="label">EVENT LOG</p><h2>网关日志</h2></div></div>
          {logs.length ? logs.slice(0, 6).map((log, index) => (
            <p className={`log ${log.level}`} key={`${log.at}-${index}`}>
              <time>{formatTime(log.at)}</time>{log.message}
            </p>
          )) : <p className="empty">等待网关事件。</p>}
        </article>
      </section>

      <footer>ROS2 Web Gateway v0.1 · 本地实验环境，不用于真实机器人安全控制。</footer>
    </main>
  );
}
