#include "importpage.hpp"
#include "ui_importpage.h"

ImportPage::ImportPage(QWidget *parent)
    : QWidget(parent), ui(new Ui::ImportPage) {
  ui->setupUi(this);
}

ImportPage::~ImportPage() { delete ui; }

void ImportPage::on_pb_open_dir_clicked() {
  QDir dir = QFileDialog::getExistingDirectory(this, "Открыть директорию",
                                               QDir::homePath());
  emit directory(dir);
}

void ImportPage::on_pb_open_files_clicked() {}
