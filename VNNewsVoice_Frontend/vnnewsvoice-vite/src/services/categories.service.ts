import { apiGet } from "./apiClient";
import type { ApiParams, Category } from "../types";

export const getCategories = (params: ApiParams = {}) =>
  apiGet<Category[]>("/categories", {
    params: {
      isActive: true,
      ...params,
    },
  });
