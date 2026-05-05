import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import MySpinner from "../../../components/layouts/MySpinner";
import { useAuth } from "../auth-context";

type RequireAuthProps = {
  children: ReactNode;
};

const RequireAuth = ({ children }: RequireAuthProps) => {
  const { isAuthenticated, isAuthLoading } = useAuth();
  const location = useLocation();

  if (isAuthLoading) {
    return <MySpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default RequireAuth;
