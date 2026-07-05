export interface EmployeePublic {
  id: string;
  user_id: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  role_name: string;
  phone: string | null;
  job_title: string | null;
  profile_picture_url: string | null;
  date_of_joining: string | null;
  employment_status: string;
  department_id: string | null;
  department_name: string | null;
  branch_name: string | null;
  manager_id: string | null;
  manager_name: string | null;
  is_active: boolean;
}

export interface PaginatedEmployees {
  items: EmployeePublic[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateEmployeePayload {
  email: string;
  password: string;
  employee_code: string;
  first_name: string;
  last_name: string;
  phone?: string;
  job_title?: string;
  date_of_joining?: string;
  department_id?: string;
  manager_id?: string;
  role: "employee" | "admin";
}

export interface UpdateEmployeePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
  job_title?: string;
  date_of_joining?: string;
  department_id?: string;
  manager_id?: string;
  employment_status?: string;
}
