export enum DebtType {
    I_OWE = 'i_owe',
    OWE_ME = 'owe_me',
}

export enum DebtStatus {
    OPEN = 'open',
    OVERDUE = 'overdue',
    PAID = 'settled',
}

export interface Debt {
    id: string;
    type: DebtType;
    person_name: string;
    amount: string;
    currency: string;
    description: string;
    due_date: string;
    user_id: string;
    status: DebtStatus;
    settled_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface DebtCreateData {
    type: DebtType;
    person_name: string;
    amount: number;
    currency: string;
    description: string;
    due_date?: string | null;
}

export interface DebtUpdateData {
    person_name: string;
    amount: number;
    description: string;
    status: DebtStatus;
    due_date?: string | null;
    settled_at: string | null;
}

export interface DebtFormData {
    type: DebtType;
    person_name: string;
    amount: number;
    currency: string;
    description: string;
    due_date: string;
}

export interface DebtBalance {
    i_owe_total: string;
    owe_me_total: string;
    i_owe_count: number;
    owe_me_count: number;
}
