package com.example.exceptions;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import com.example.exceptions.ErrorResponse;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AccountNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(AccountNotFoundException ex) {
        return new ResponseEntity<ErrorResponse>(
                new ErrorResponse(ex.getMessage(), 404, LocalDateTime.now()),
                HttpStatus.NOT_FOUND
        );
    }

    @ExceptionHandler(DuplicateAccountException.class)
    public ResponseEntity<ErrorResponse> handleDuplicate(DuplicateAccountException ex) {
        return new ResponseEntity<ErrorResponse>(
                new ErrorResponse(ex.getMessage(), 409, LocalDateTime.now()),
                HttpStatus.CONFLICT
        );
    }
    @ExceptionHandler(InvalidAccountNumberException.class)
    public ResponseEntity<ErrorResponse> invalidAccountNumber(InvalidAccountNumberException ex) {
        return new ResponseEntity<ErrorResponse>(
                new ErrorResponse(ex.getMessage(), 410, LocalDateTime.now()),
                HttpStatus.GONE
        );
    }
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(Exception ex) {
        return new ResponseEntity<ErrorResponse>(
                new ErrorResponse("Something went wrong", 500, LocalDateTime.now()),
                HttpStatus.INTERNAL_SERVER_ERROR
        );
    }
}