import { createContext, useContext, useEffect, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
	const [user, setUser] = useState(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		if (!localStorage.getItem("stocksense_token")) {
			setLoading(false);
			return;
		}
		api.get("/auth/me").then(({ data }) => setUser(data)).catch(() => localStorage.removeItem("stocksense_token")).finally(() => setLoading(false));
	}, []);

	async function login(email, password) {
		const { data } = await api.post("/auth/login", { email, password });
		localStorage.setItem("stocksense_token", data.access_token);
		setUser((await api.get("/auth/me")).data);
	}

	function logout() {
		localStorage.removeItem("stocksense_token");
		setUser(null);
	}

	return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
	return useContext(AuthContext);
}
