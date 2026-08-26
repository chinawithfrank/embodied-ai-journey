'use client';

import { FormEvent, useCallback, useEffect, useState } from 'react';

import { RobotScene } from '../components/RobotScene';

type Position = { x: number; y: number; z: number };
type Task = {
  id: string;
  pick: Position;
  place: Position;
  status: string;
  message: string;
  progress: number;
  created_at: string;
};
type Status = { ros_available: boolean; robot_online: boolean; ros_reason: string | null };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8001';
const rosUrl = process.env.NEXT_PUBLIC_ROSBRIDGE_URL ?? 'ws://localhost:9092';
const defaultPick = { x: 0.45, y: -0.2, z: 0.03 };
const defaultPlace = { x: 0.25, y: 0.35, z: 0.03 };

function CoordinateFields({
  label,
  value,
  onChange,
}: {
  label: string;
  value: Position;
  onChange: (value: Position) => void;
}) {
  return <fieldset>
    <legend>{label}</legend>
    {(['x', 'y', 'z'] as const).map((axis) => <label key={axis}>
      {axis.toUpperCase()}
      <input
        type="number"
        step="0.01"
        value={value[axis]}
        onChange={(event) => onChange({
          ...value,
          [axis]: Number(event.target.value),
        })}
      />
    </label>)}
  </fieldset>;
}

export default function Home() {
  const [pick, setPick] = useState<Position>(defaultPick);
  const [place, setPlace] = useState<Position>(defaultPlace);
  const [status, setStatus] = useState<Status | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [nextStatus, nextTasks] = await Promise.all([
        fetch(`${apiUrl}/api/status`).then((response) => response.json()),
        fetch(`${apiUrl}/api/tasks`).then((response) => response.json()),
      ]);
      setStatus(nextStatus as Status);
      setTasks(nextTasks as Task[]);
      setError('');
    } catch {
      setError('无法连接 MoveIt Web Gateway。请确认后端和 ROS2 launch 均已启动。');
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 1500);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const response = await fetch(`${apiUrl}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pick, place }),
      });
      if (!response.ok) throw new Error();
      await refresh();
    } catch {
      setError('任务提交失败：请检查坐标是否在演示工作空间内。');
    }
  }

  const activeTask = tasks[0];
  return <main>
    <header>
      <div><p className="eyebrow">MONTH 02 · FINAL BUILD</p><h1>MoveIt <em>Web Studio</em></h1>
        <p>在浏览器中创建 Panda 的抓取、搬运与放置任务。</p></div>
      <div className={status?.robot_online ? 'badge online' : 'badge'}>
        <i /> {status?.robot_online ? '机器人在线' : '等待机器人'}
      </div>
    </header>
    {error && <p className="error">{error}</p>}
    <section className="workspace">
      <article className="scene"><RobotScene
        pick={activeTask?.pick ?? pick}
        place={activeTask?.place ?? place}
        rosUrl={rosUrl}
        assetUrl={apiUrl}
        taskStatus={activeTask?.status}
      />
        <div className="scene-key"><span className="pick-dot" />抓取物 <span className="place-dot" />放置目标</div>
      </article>
      <aside className="task-panel">
        <p className="eyebrow">TASK BUILDER</p><h2>创建抓取任务</h2>
        <p className="muted">仅允许工作空间内的取放坐标；MoveIt 仍负责规划、避碰和执行。</p>
        <form onSubmit={submit}>
          <CoordinateFields label="抓取位置 (m)" value={pick} onChange={setPick} />
          <CoordinateFields label="放置位置 (m)" value={place} onChange={setPlace} />
          <button disabled={!status?.ros_available}>规划并执行</button>
        </form>
        <div className="connection"><b>ROSLIB</b><span>{rosUrl}</span></div>
      </aside>
    </section>
    <section className="status-grid">
      <article><p className="eyebrow">MOVEIT TASK</p><h2>{activeTask?.status ?? '尚无任务'}</h2>
        <p>{activeTask?.message ?? '填写取放坐标后提交第一个任务。'}</p>
        <div className="progress"><i style={{ width: `${activeTask?.progress ?? 0}%` }} /></div>
        <small>{activeTask ? `${activeTask.progress.toFixed(0)}% · ${activeTask.id}` : '等待任务'}</small>
      </article>
      <article><p className="eyebrow">ROS2 CONNECTION</p><h2>{status?.ros_available ? 'Gateway 已连接' : 'Gateway 未连接'}</h2>
        <p>{status?.ros_reason ?? '正在通过 ROSLIB 接收 /joint_states。'}</p>
      </article>
    </section>
    <footer>本地 Panda mock 环境 · 仅用于学习与演示，不用于真实机械臂安全控制。</footer>
  </main>;
}
