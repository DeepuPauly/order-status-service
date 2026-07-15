import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getOrders() {
  const res = await fetch(`${API}/api/orders/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load orders");
  return res.json();
}

export default async function Home() {
  const { orders } = await getOrders();

  return (
    <main>
      <h1 style={{ fontSize: 24, marginBottom: 20 }}>Orders</h1>
      {orders.length === 0 ? (
        <p>No orders yet. Run the seed script to add some.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "2px solid #e5e7eb" }}>
              <th style={{ padding: "10px 12px" }}>Order</th>
              <th style={{ padding: "10px 12px" }}>Status</th>
              <th style={{ padding: "10px 12px" }}>Last source</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.order_id} style={{ borderBottom: "1px solid #eee" }}>
                <td style={{ padding: "10px 12px" }}>
                  <Link href={`/orders/${o.order_id}`} style={{ color: "#2563eb" }}>
                    {o.order_id}
                  </Link>
                </td>
                <td style={{ padding: "10px 12px" }}>{o.status}</td>
                <td style={{ padding: "10px 12px" }}>{o.last_source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}