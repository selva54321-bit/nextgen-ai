package com.ai_nextgen_hacks.main.models;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    private String orderId;
    private String customerId;
    private LocalDateTime createdAt;
    private String status; // e.g., PENDING, PICKING, READY, DISPATCHED
    private LocalDateTime deadline;

    public Order() {}

    public Order(String orderId, String customerId, LocalDateTime createdAt, String status, LocalDateTime deadline) {
        this.orderId = orderId;
        this.customerId = customerId;
        this.createdAt = createdAt;
        this.status = status;
        this.deadline = deadline;
    }

    public String getOrderId() { return orderId; }
    public void setOrderId(String orderId) { this.orderId = orderId; }

    public String getCustomerId() { return customerId; }
    public void setCustomerId(String customerId) { this.customerId = customerId; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public LocalDateTime getDeadline() { return deadline; }
    public void setDeadline(LocalDateTime deadline) { this.deadline = deadline; }
}
