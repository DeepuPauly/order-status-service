import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getOrder(orderId) {
  const res = await fetch(`${API}/api/orders/${orderId}/`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to load order");
  return res.json();
}

export default async function OrderDetail({ params }) {
  const { orderId } = await params; // in Next 15 params is async; awaiting is required
  const order = await getOrder(orderId);

  if (!order) {
    return (
      <main>
        <p>Order not found.</p>
        <Link href="/" style={{ color: "#2563eb" }}>← Back to all orders</Link>
      </main>
    );
  }

  return (
    <main>
      <Link href="/" style={{ color: "#2563eb" }}>← Back to all orders</Link>
      <h1 style={{ fontSize: 24, margin: "16px 0" }}>Order {order.order_id}</h1>
      <div style={{ background: "#fff", padding: 20, borderRadius: 8 }}>
        <Row label="Current status" value={order.status} />
        <Row label="Last updated by" value={order.last_source} />
        <Row
          label="Status timestamp"
          value={new Date(order.status_event_timestamp).toUTCString()}
        />
        <Row
          label="Record updated"
          value={new Date(order.updated_at).toUTCString()}
        />
      </div>
    </main>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: "flex", padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
      <div style={{ width: 160, color: "#666" }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  );
}