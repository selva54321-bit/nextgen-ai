package com.ai_nextgen_hacks.main.controllers;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/delivery")
public class DeliveryController {

    @PostMapping("/predictions")
    public ResponseEntity<String> persistDeliveryPrediction() {
        return ResponseEntity.ok("{\"status\": \"PREDICTION_SAVED\"}");
    }

    @GetMapping("/stops/{id}/risk")
    public ResponseEntity<String> getRisk(@PathVariable String id) {
        return ResponseEntity.ok("{\"stopId\": \"" + id + "\", \"riskBand\": \"MEDIUM\", \"failureProbability\": 0.034}");
    }

    @PostMapping("/events")
    public ResponseEntity<String> recordDeliveryEvent() {
        return ResponseEntity.ok("{\"status\": \"EVENT_RECORDED\"}");
    }
}
