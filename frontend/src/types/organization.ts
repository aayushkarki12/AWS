export interface BranchPublic {
  id: string;
  name: string;
  code: string;
  address: string | null;
  timezone: string;
}

export interface DepartmentPublic {
  id: string;
  name: string;
  code: string;
  branch_id: string;
}
