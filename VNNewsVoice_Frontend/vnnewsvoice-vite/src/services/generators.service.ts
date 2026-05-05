import { apiGet } from "./apiClient";
import type { ApiParams, Generator } from "../types";

export const getGenerators = (params?: ApiParams) =>
  apiGet<Generator[]>("/generators", { params });
