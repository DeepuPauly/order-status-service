export const metadata = { title: "Order Status" };

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        suppressHydrationWarning
        style={{
          fontFamily: "system-ui, -apple-system, sans-serif",
          margin: 0,
          background: "#f6f7f9",
          color: "#1a1a1a",
        }}
      >
        <div style={{ maxWidth: 820, margin: "0 auto", padding: "32px 20px" }}>
          {children}
        </div>
      </body>
    </html>
  );
}