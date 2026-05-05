import type { ReactNode } from "react";
import { useState } from "react";
import { SearchContext } from "./searchContextStore";

type SearchContextProviderProps = {
  children: ReactNode;
};

const SearchContextProvider = ({ children }: SearchContextProviderProps) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedGenerator, setSelectedGenerator] = useState("");

  return (
    <SearchContext.Provider
      value={{
        searchTerm,
        setSearchTerm,
        selectedCategory,
        setSelectedCategory,
        selectedGenerator,
        setSelectedGenerator,
      }}
    >
      {children}
    </SearchContext.Provider>
  );
};

export { SearchContextProvider };

