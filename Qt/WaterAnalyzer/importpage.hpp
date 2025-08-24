#ifndef IMPORTPAGE_HPP
#define IMPORTPAGE_HPP

#include <QDir>
#include <QFileDialog>
#include <QWidget>

namespace Ui {
class ImportPage;
}

class ImportPage : public QWidget {
  Q_OBJECT

public:
  explicit ImportPage(QWidget *parent = nullptr);
  ~ImportPage();

private slots:
  void on_pb_open_dir_clicked();
  void on_pb_open_files_clicked();

signals:
  void directory(QDir);

private:
  Ui::ImportPage *ui;
};

#endif // IMPORTPAGE_HPP
