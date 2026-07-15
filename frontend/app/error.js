"use client";

export default function Error({ error, reset }) {
  return (
    <main>
      <h1 style={{ fontSize: 20, marginBottom: 8 }}>Couldn't load orders</h1>
      <p style={{ color: "#666", marginBottom: 16 }}>
        Is the backend running on http://localhost:8000?
      </p>
      <button
        onClick={reset}
        style={{
          padding: "8px 14px",
          border: "1px solid #d1d5db",
          borderRadius: 6,
          background: "#fff",
          cursor: "pointer",
        }}
      >
        Try again
      </button>
    </main>
  );
}