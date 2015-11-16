cask :v1 => 'menubargmail' do
  version '0.0.1'
  sha256 '881e1651443f18c79a75574173006eb3f00686f2e78fffe83e42317cda45b3c5'

  url "https://github.com/rcmdnk/MenuBarGmail/archive/MenuBarGmail_v#{version}.zip"
  name 'MenuBarGmail'
  homepage 'https://github.com/rcmdnk/MenuBarGmail'
  license :mit

  app 'MenuBarGmail.app'
end
