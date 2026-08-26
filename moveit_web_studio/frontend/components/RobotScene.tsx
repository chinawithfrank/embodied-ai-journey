'use client';

import { Grid, OrbitControls } from '@react-three/drei';
import { Canvas, useFrame } from '@react-three/fiber';
import * as ROSLIB from 'roslib';
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import URDFLoader from 'urdf-loader';

type Position = { x: number; y: number; z: number };

type JointState = Record<string, number>;

function PandaUrdf({ joints }: { joints: JointState }) {
  const [robot, setRobot] = useState<THREE.Object3D | null>(null);

  useEffect(() => {
    const loader = new URDFLoader();
    loader.load('/robot/panda_web.urdf', setRobot);
  }, []);

  useFrame(() => {
    const urdfRobot = robot as THREE.Object3D & {
      joints?: Record<string, { setJointValue: (value: number) => void }>;
    };
    for (const [name, value] of Object.entries(joints)) {
      urdfRobot.joints?.[name]?.setJointValue(value);
    }
  });

  return robot ? <primitive object={robot} rotation-x={-Math.PI / 2} /> : null;
}

function LiveRobot({ rosUrl }: { rosUrl: string }) {
  const [joints, setJoints] = useState<JointState>({});

  useEffect(() => {
    const ros = new ROSLIB.Ros({ url: rosUrl });
    const topic = new ROSLIB.Topic({
      ros,
      name: '/joint_states',
      messageType: 'sensor_msgs/msg/JointState',
    });
    topic.subscribe((message) => {
      const jointMessage = message as unknown as {
        name: string[];
        position: number[];
      };
      setJoints(Object.fromEntries(
        jointMessage.name.map((name, index) => [
          name,
          jointMessage.position[index] ?? 0,
        ]),
      ));
    });
    return () => {
      topic.unsubscribe();
      ros.close();
    };
  }, [rosUrl]);

  return <PandaUrdf joints={joints} />;
}

function TaskMarkers({
  pick,
  place,
  taskStatus,
}: {
  pick: Position;
  place: Position;
  taskStatus?: string;
}) {
  const object = useRef<THREE.Mesh>(null);
  const isCarried = ['transporting', 'placing', 'returning', 'succeeded'].includes(
    taskStatus ?? '',
  );

  useFrame(() => {
    const target = isCarried ? place : pick;
    object.current?.position.lerp(
      new THREE.Vector3(target.x, target.z, -target.y),
      0.04,
    );
  });

  return <>
    <mesh ref={object} position={[pick.x, pick.z, -pick.y]}>
      <boxGeometry args={[0.05, 0.05, 0.05]} />
      <meshStandardMaterial color="#ff8a3d" />
    </mesh>
    <mesh position={[place.x, place.z, -place.y]}>
      <cylinderGeometry args={[0.055, 0.055, 0.012, 32]} />
      <meshStandardMaterial color="#65d6ff" />
    </mesh>
  </>;
}

export function RobotScene({
  pick,
  place,
  rosUrl,
  taskStatus,
}: {
  pick: Position;
  place: Position;
  rosUrl: string;
  taskStatus?: string;
}) {
  return <Canvas camera={{ position: [1.25, 0.9, 1.25], fov: 42 }}>
    <color attach="background" args={['#10151a']} />
    <ambientLight intensity={1.5} />
    <directionalLight position={[3, 5, 3]} intensity={2.2} castShadow />
    <Grid args={[2, 2]} cellColor="#2d3742" sectionColor="#51606e" />
    <TaskMarkers pick={pick} place={place} taskStatus={taskStatus} />
    <LiveRobot rosUrl={rosUrl} />
    <OrbitControls makeDefault minDistance={0.8} maxDistance={3} />
  </Canvas>;
}
