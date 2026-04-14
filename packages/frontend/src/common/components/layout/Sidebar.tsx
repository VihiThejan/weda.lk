import { NavLink } from "react-router-dom";
import type { CSSProperties } from "react";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/maintenance", label: "Maintenance" },
];

export function Sidebar() {
  return (
    <aside style={styles.sidebar}>
      <div style={styles.brand}>MSP Platform</div>
      <nav style={styles.nav}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              ...styles.link,
              backgroundColor: isActive ? "#0b6e4f" : "transparent",
              color: isActive ? "#ffffff" : "#deebe7",
            })}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

const styles: Record<string, CSSProperties> = {
  sidebar: {
    width: "250px",
    minHeight: "100vh",
    backgroundColor: "#13312a",
    padding: "20px 14px",
  },
  brand: {
    fontWeight: 700,
    color: "#ecf3f1",
    letterSpacing: "0.2px",
    marginBottom: "18px",
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  link: {
    borderRadius: "10px",
    padding: "10px 12px",
    fontSize: "14px",
    transition: "all 180ms ease",
  },
};
