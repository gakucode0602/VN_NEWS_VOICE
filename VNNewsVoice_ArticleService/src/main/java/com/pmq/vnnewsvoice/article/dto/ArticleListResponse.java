package com.pmq.vnnewsvoice.article.dto;

import com.pmq.vnnewsvoice.article.utils.Pagination;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleListResponse {
  private List<ArticleResponse> articles;
  private Pagination pagination;
}
