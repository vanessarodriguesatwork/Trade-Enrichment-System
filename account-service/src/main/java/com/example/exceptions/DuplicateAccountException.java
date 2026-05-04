package com.example.exceptions;
public class DuplicateAccountException extends RuntimeException {
    public DuplicateAccountException(String accNo) {
        super("Account already exists with number: " + accNo);
    }
}