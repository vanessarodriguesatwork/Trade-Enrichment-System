package com.example.exceptions;

public class InvalidXmlException extends RuntimeException {
    public InvalidXmlException(String message) {
        super(message);
    }
}