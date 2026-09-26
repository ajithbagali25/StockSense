import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navigation = [
	["Dashboard", "/"],
	["Products", "/products"],
	["Receipts", "/receipts"],
	["Deliveries", "/deliveries"],
	["Transfers", "/transfers"],
	["Adjustments", "/adjustments"],
	["Stock Ledger", "/ledger"],
];

export default function MainLayout() {
	const { user, logout } = useAuth();
	return (
		<div className="app-shell">
			<aside className="sidebar">
				<div className="brand"><span className="brand-mark">S</span><span>StockSense</span></div>
				<nav>{navigation.map(([label, path]) => <NavLink key={path} to={path} end={path === "/"}>{label}</NavLink>)}</nav>
				<div className="sidebar-footer"><small>{user?.role?.replaceAll("_", " ")}</small><button onClick={logout}>Log out</button></div>
			</aside>
			<main className="main-area"><header><div><span className="eyebrow">Inventory control center</span><h1>Good morning, {user?.full_name?.split(" ")[0]}</h1></div><div className="avatar">{user?.full_name?.[0]}</div></header><Outlet /></main>
		</div>
	);
}
