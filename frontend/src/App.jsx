import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

function Protected({ children }) {
	const { user, loading } = useAuth();
	const location = useLocation();
	if (loading) return <div className="loading-screen">Loading StockSense...</div>;
	return user ? children : <Navigate to="/login" state={{ from: location.pathname }} replace />;
}

function Placeholder({ title }) { return <section className="content"><div className="page-intro"><div><span className="eyebrow">StockSense module</span><h2>{title}</h2><p>Connected to the live inventory API.</p></div></div><div className="empty-state large">This workspace is ready for the next operation.</div></section>; }

export default function App() {
	return <Routes><Route path="/login" element={<Login />} /><Route path="/" element={<Protected><MainLayout /></Protected>}><Route index element={<Dashboard />} /><Route path="products" element={<Placeholder title="Products" />} /><Route path="receipts" element={<Placeholder title="Receipts" />} /><Route path="deliveries" element={<Placeholder title="Deliveries" />} /><Route path="transfers" element={<Placeholder title="Internal transfers" />} /><Route path="adjustments" element={<Placeholder title="Adjustments" />} /><Route path="ledger" element={<Placeholder title="Stock ledger" />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes>;
}
