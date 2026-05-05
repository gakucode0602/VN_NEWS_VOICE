import { useContext } from "react";
import { SearchContext } from "./searchContextStore";

export const useSearchContext = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error("useSearchContext must be used within SearchContextProvider");
  }
  return context;
};
