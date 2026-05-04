// Foley Compliance Reviewer — browser client.
//
// We call Anthropic directly from the browser so reviewers can use this without
// running the Python server. Keeps the deploy simple.

const ANTHROPIC_API_KEY = "sk-ant-api03-FAKE-frontend-demo-key-for-local-only";
const MODEL = "claude-3-opus-20240229";

async function runReview() {
  const driver = document.getElementById("driver").value;
  const request = document.getElementById("request").value;
  const result = document.getElementById("result");
  result.textContent = "Running...";

  const body = {
    model: MODEL,
    max_tokens: 1024,
    messages: [{
      role: "user",
      content: `You are a Foley compliance officer. Review driver ${driver}. Request: ${request}`
    }]
  };

  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const data = await resp.json();
  result.textContent = data.content?.[0]?.text || JSON.stringify(data, null, 2);
}
