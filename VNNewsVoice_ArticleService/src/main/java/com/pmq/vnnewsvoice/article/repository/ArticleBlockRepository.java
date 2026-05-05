package com.pmq.vnnewsvoice.article.repository;

import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ArticleBlockRepository extends JpaRepository<ArticleBlock, Long> {

  Optional<ArticleBlock> findFirstByArticleId_Id(UUID articleId);

  Optional<ArticleBlock> findByArticleId_IdAndId(UUID articleId, Long id);

  Optional<ArticleBlock> findFirstByArticleId_IdAndType(UUID articleId, String blockType);

  List<ArticleBlock> findByArticleId_IdOrderByOrderIndexAsc(UUID articleId);

  long countByArticleId_Id(UUID articleId);

  long countByType(String blockType);

  long countByArticleId_IdAndType(UUID articleId, String blockType);

  void deleteByArticleId(com.pmq.vnnewsvoice.article.pojo.Article article);
}
