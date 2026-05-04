package com.example.exceptions;

public class AccountNotFoundException extends RuntimeException {
    public AccountNotFoundException(String accNo) {
        super("Account not found with number: " + accNo);
    }
}