cask :v1 => 'menubargmail' do
  version '0.0.1'
  sha256 ''

  url '#{version}.zip'
  name 'MenuBarGmail'
  homepage 'https://github.com/rcmdnk/MenuBarGmail'
  license :mit

  app 'MenuBarGmail.app'
end
