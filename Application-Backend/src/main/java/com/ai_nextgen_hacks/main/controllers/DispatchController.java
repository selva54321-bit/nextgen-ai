package com.ai_nextgen_hacks.main.controllers;

import com.ai_nextgen_hacks.main.dtos.DispatchPlanRequest;
import com.ai_nextgen_hacks.main.dtos.DispatchPlanResponse;
import com.ai_nextgen_hacks.main.services.DispatchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/dispatch")
public class DispatchController {

    @Autowired
    private DispatchService dispatchService;

    @PostMapping("/plan")
    public ResponseEntity<?> planDispatch(@RequestBody DispatchPlanRequest request) {
        try {
            DispatchPlanResponse response = dispatchService.planDispatch(request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }
}
