package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.AdminDashboardStatisticsResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.service.AdminStatisticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/admin")
@PreAuthorize("hasRole('ADMIN')")
public class ApiAdminStatisticsController {

  private final AdminStatisticsService adminStatisticsService;

  /**
   * GET /api/secure/admin/statistics
   *
   * <p>Returns a consolidated dashboard snapshot:
   *
   * <ul>
   *   <li>Overview counters: total articles, likes, categories, generators
   *   <li>Recency counters: articles published in the last 7 / 30 days
   *   <li>Breakdowns: articles grouped by status, category, and generator
   * </ul>
   */
  @GetMapping("/statistics")
  public ResponseEntity<ApiResponse<AdminDashboardStatisticsResponse>> getDashboardStatistics(
      @RequestParam(defaultValue = "7") int days) {
    AdminDashboardStatisticsResponse stats = adminStatisticsService.getDashboardStatistics(days);
    return ResponseEntity.ok(ApiResponse.ok("Dashboard statistics retrieved successfully", stats));
  }
}
