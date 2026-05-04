package com.example.demo.exceptions;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.example.exceptions.InvalidXmlException;
import com.example.exceptions.RecoverableException;

class ExceptionTests {

    @Test
    void testInvalidXmlException() {
        InvalidXmlException ex = new InvalidXmlException("Bad XML");
        assertEquals("Bad XML", ex.getMessage());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testRecoverableException() {
        Throwable cause = new RuntimeException("Connection refused");
        RecoverableException ex = new RecoverableException("Network issue", cause);

        assertEquals("Network issue", ex.getMessage());
        assertEquals(cause, ex.getCause());
        assertInstanceOf(RuntimeException.class, ex);
    }

    @Test
    void testRecoverableException_WithDifferentCause() {
        Throwable cause = new java.io.IOException("Timeout");
        RecoverableException ex = new RecoverableException("Service timeout", cause);

        assertEquals("Service timeout", ex.getMessage());
        assertInstanceOf(java.io.IOException.class, ex.getCause());
    }
}
