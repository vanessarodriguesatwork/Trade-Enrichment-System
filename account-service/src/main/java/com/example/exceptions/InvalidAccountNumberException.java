package com.example.exceptions;

public class InvalidAccountNumberException extends RuntimeException {
    public InvalidAccountNumberException(String accNo) {
        super("Invalid account number: " + accNo + " (must be numeric)");
    }
}