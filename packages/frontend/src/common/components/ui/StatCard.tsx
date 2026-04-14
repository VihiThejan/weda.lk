import type { CSSProperties } from "react";

type StatCardProps = {
  label: string;
  value: string;
  note?: string;
};

export function StatCard({ label, value, note }: StatCardProps) {
  return (
    <article style={styles.card}>
      <p style={styles.label}>{label}</p>
      <p style={styles.value}>{value}</p>
      {note ? <p style={styles.note}>{note}</p> : null}
    </article>
  );
}

const styles: Record<string, CSSProperties> = {
  card: {
    border: "1px solid #d4dae2",
    borderRadius: "12px",
    backgroundColor: "#fbfcfd",
    padding: "14px",
    minWidth: "180px",
  },
  label: {
    margin: 0,
    color: "#52606d",
    fontSize: "13px",
  },
  value: {
    margin: "6px 0",
    fontSize: "24px",
    fontWeight: 700,
    color: "#1b2430",
  },
  note: {
    margin: 0,
    color: "#6b7785",
    fontSize: "12px",
  },
};
