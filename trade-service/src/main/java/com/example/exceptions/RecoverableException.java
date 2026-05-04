package com.example.exceptions;

public class RecoverableException extends RuntimeException {
    public RecoverableException(String message, Throwable cause) {
        super(message, cause);
    }
}