# ROS2 Web Gateway v0.1

第一个月的交付产品：一个面向本地实验的 ROS2 运行控制台。

它只暴露白名单能力：读取 `/joint_states`、调用 `/set_motors_enabled`、创建/取消 `/turtle1/rotate_absolute` Action，并录制 `/joint_states` 与 `/visualization_marker` 为 MCAP。

在 Ubuntu 上从仓库根目录启动：

```bash
docker compose --env-file web_gateway/.env.example \
  -f web_gateway/docker-compose.yml up --build
```

打开 `http://localhost:3001`。完整的架构、验收步骤、API 和安全边界见 [`notes/01-Fundamentals/06-ROS2-Web-Gateway`](../notes/01-Fundamentals/06-ROS2-Web-Gateway)。
