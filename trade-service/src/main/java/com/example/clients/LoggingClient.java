package com.example.clients;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.*;

import com.example.entities.EnrichedTrade;
import com.example.exceptions.RecoverableException;

@Component
public class LoggingClient {

    @Value("${logging.service.url}")
    private String loggingUrl;

    private final RestTemplate restTemplate = new RestTemplate();

    public void send(EnrichedTrade trade) {

        try {
            restTemplate.postForObject(loggingUrl, trade, String.class);
            System.out.println("Sent to Logging Service");

        } catch (ResourceAccessException ex) {
            throw new RecoverableException("Logging service network error", ex);

        } catch (HttpServerErrorException ex) {
            throw new RecoverableException("Logging service server error", ex);

        } catch (HttpClientErrorException ex) {
            System.out.println("Logging failed (non-recoverable)");
        }
    }
}