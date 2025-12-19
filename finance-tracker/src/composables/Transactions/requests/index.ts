import $axios from "@/api";
import type { Transaction, TransactionsResponse, GetTransactionsParams, TransactionCreateData, TransactionUpdateData } from "../types";

export const useTransactionsRequests = () => {
    const getTransactions = async (params?: GetTransactionsParams): Promise<TransactionsResponse> => {
        try {
            const response = await $axios.get<TransactionsResponse>('/transactions', { params });
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }

    const getTransaction = async (id: string): Promise<Transaction> => {
        try {
            const response = await $axios.get<Transaction>(`/transactions/${id}`);
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }

    const createTransaction = async (transaction: TransactionCreateData): Promise<Transaction> => {
        try {
            const response = await $axios.post<Transaction>('/transactions', transaction);
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }

    const updateTransaction = async (id: string, transaction: TransactionUpdateData): Promise<Transaction> => {
        try {
            const response = await $axios.patch<Transaction>(`/transactions/${id}`, transaction);
            return response.data;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }

    const deleteTransaction = async (id: string): Promise<void> => {
        try {
            await $axios.delete(`/transactions/${id}`);
        } catch (error) {
            console.error(error);
            throw error;
        }
    }

    return {
        getTransactions,
        getTransaction,
        createTransaction,
        updateTransaction,
        deleteTransaction,
    }
}
