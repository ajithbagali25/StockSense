import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
	const { user, login } = useAuth();
	const navigate = useNavigate();
	const location = useLocation();
	const [email, setEmail] = useState("manager@example.com");
	const [password, setPassword] = useState("");
	const [error, setError] = useState("");
	if (user) return <Navigate to={location.state?.from || "/"} replace />;

	async function submit(event) {
		event.preventDefault();
		setError("");
		try { await login(email, password); navigate("/"); } catch { setError("We could not sign you in. Check your email and password."); }
	}

	return <div className="login-page"><div className="login-panel"><div className="brand"><span className="brand-mark">S</span><span>StockSense</span></div><span className="eyebrow">Inventory intelligence</span><h1>Know what is moving.</h1><p>One clear view of every product, location, and stock decision.</p><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <div className="error-message">{error}</div>}<button className="primary-button" type="submit">Sign in</button></form></div><div className="login-art"><span>LIVE INVENTORY</span><strong>225 units<br />moving today</strong><div className="pulse-line" /></div></div>;
}
