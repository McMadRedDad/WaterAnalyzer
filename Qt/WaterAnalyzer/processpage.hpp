#ifndef PROCESSPAGE_HPP
#define PROCESSPAGE_HPP

#include <QWidget>

namespace Ui {
class ProcessPage;
}

class ProcessPage : public QWidget {
  Q_OBJECT

public:
  explicit ProcessPage(QWidget *parent = nullptr);
  ~ProcessPage();

private slots:
  void on_pb_refresh_clicked();

private:
  Ui::ProcessPage *ui;
};

#endif // PROCESSPAGE_HPP
