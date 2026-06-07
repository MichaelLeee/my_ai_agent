import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({
    serviceName: "my_ai_agent-frontend",
  });
}
