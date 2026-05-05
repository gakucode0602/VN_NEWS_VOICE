export interface Generator {
  id: number;
  name: string;
  logoUrl?: string | null;
  url?: string | null;
  isActive?: boolean | null;
}
