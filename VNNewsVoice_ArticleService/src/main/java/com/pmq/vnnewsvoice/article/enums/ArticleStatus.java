package com.pmq.vnnewsvoice.article.enums;

public enum ArticleStatus {
  DRAFT("Draft"),
  PUBLISHED("Published"),
  PENDING("Pending"),
  REJECTED("Rejected"),
  DELETED("Deleted");

  private final String status;

  ArticleStatus(String status) {
    this.status = status;
  }

  public String getStatus() {
    return status;
  }

  @Override
  public String toString() {
    return status;
  }
}
