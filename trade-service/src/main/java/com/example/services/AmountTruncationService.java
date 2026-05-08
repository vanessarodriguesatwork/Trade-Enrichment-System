package com.example.services;

import java.math.BigDecimal;
import java.math.RoundingMode;

import org.springframework.stereotype.Service;
@Service
public class AmountTruncationService {
    
    public BigDecimal truncateToTwoDecimalPlaces(String amount) {
        if (amount == null || amount.isEmpty()) {
            throw new IllegalArgumentException("Amount cannot be null or empty");
        }

        BigDecimal value = new BigDecimal(amount);
        return value.setScale(2, RoundingMode.DOWN);
    }
}
