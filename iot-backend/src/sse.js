// SSE (Server-Sent Events) — day du lieu realtime xuong dashboard
// KHONG dung WebSocket vi SSE don gian hon, chi can 1 chieu server->browser
// la du cho yeu cau "khong bam F5" cua rubric.

const clients = new Set();

function addClient(res) {
  clients.add(res);
}

function removeClient(res) {
  clients.delete(res);
}

function broadcast(eventName, data) {
  const payload = `event: ${eventName}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const res of clients) {
    res.write(payload);
  }
}

module.exports = { addClient, removeClient, broadcast };
