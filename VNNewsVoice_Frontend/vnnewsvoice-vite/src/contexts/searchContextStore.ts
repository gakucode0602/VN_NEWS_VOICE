import { createContext } from "react";
import type { Dispatch, SetStateAction } from "react";

export type SearchContextValue = {
  searchTerm: string;
  setSearchTerm: Dispatch<SetStateAction<string>>;
  selectedCategory: string;
  setSelectedCategory: Dispatch<SetStateAction<string>>;
  selectedGenerator: string;
  setSelectedGenerator: Dispatch<SetStateAction<string>>;
};

export const SearchContext = createContext<SearchContextValue | undefined>(undefined);
