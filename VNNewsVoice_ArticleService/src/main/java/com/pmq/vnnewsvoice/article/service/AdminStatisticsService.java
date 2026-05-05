package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.dto.AdminDashboardStatisticsResponse;

public interface AdminStatisticsService {
  AdminDashboardStatisticsResponse getDashboardStatistics(int days);
}
