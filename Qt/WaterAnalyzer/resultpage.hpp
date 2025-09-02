#ifndef RESULTPAGE_HPP
#define RESULTPAGE_HPP

#include "resulttab.hpp"
#include <QWidget>

namespace Ui {
class ResultPage;
}

class ResultPage : public QWidget {
  Q_OBJECT

public:
  explicit ResultPage(QWidget *parent = nullptr);
  ~ResultPage();

  void set_preview(QString page, QPixmap image);
  uint get_preview_width();
  uint get_preview_height();

private:
  Ui::ResultPage *ui;
  ResultTab *summary;
  ResultTab *water;
  ResultTab *chloro;
  ResultTab *tss;
  ResultTab *cdom;
  ResultTab *temp;
};

#endif // RESULTPAGE_HPP
